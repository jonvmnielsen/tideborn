#include "TidebornInteractComponent.h"
#include "TidebornInteractable.h"
#include "TidebornBuildComponent.h"
#include "EnhancedInputComponent.h"
#include "InputAction.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "Engine/World.h"
#include "TimerManager.h"
#include "DrawDebugHelpers.h"
#include "Engine/Engine.h"
#include "Engine/OverlapResult.h"
#include "CollisionQueryParams.h"

UTidebornInteractComponent::UTidebornInteractComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
	InteractDistance = 400.f;
}

void UTidebornInteractComponent::BeginPlay()
{
	Super::BeginPlay();

	if (!InteractAction)
	{
		InteractAction = LoadObject<UInputAction>(nullptr, TEXT("/Game/ThirdPerson/Input/Actions/IA_Interact.IA_Interact"));
	}

	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateUObject(this, &UTidebornInteractComponent::BindInput));
	}
}

void UTidebornInteractComponent::BindInput()
{
	if (bInputBound)
	{
		return;
	}

	APawn* Pawn = Cast<APawn>(GetOwner());
	if (!Pawn)
	{
		return;
	}

	UEnhancedInputComponent* EIC = Cast<UEnhancedInputComponent>(Pawn->InputComponent);
	if (!EIC)
	{
		if (APlayerController* PC = Cast<APlayerController>(Pawn->GetController()))
		{
			EIC = Cast<UEnhancedInputComponent>(PC->InputComponent);
		}
	}

	if (EIC && InteractAction)
	{
		EIC->BindAction(InteractAction, ETriggerEvent::Started, this, &UTidebornInteractComponent::OnInteract);
		bInputBound = true;
		UE_LOG(LogTemp, Log, TEXT("TidebornInteract: bound IA_Interact"));
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("TidebornInteract: bind deferred/failed (EIC=%d Action=%d)"), EIC != nullptr, InteractAction != nullptr);
		if (UWorld* World = GetWorld())
		{
			FTimerHandle Handle;
			World->GetTimerManager().SetTimer(Handle, this, &UTidebornInteractComponent::BindInput, 0.25f, false);
		}
	}
}

void UTidebornInteractComponent::OnInteract(const FInputActionValue& Value)
{
	TryInteract();
}

void UTidebornInteractComponent::TryInteract()
{
	AActor* Owner = GetOwner();
	if (!Owner || !GetWorld())
	{
		return;
	}

	if (UTidebornBuildComponent* Build = Owner->FindComponentByClass<UTidebornBuildComponent>())
	{
		if (Build->bBuildMode)
		{
			Build->TryCommitPlacement();
			return;
		}
	}

	// Trace from the camera (what you look at), not the body facing.
	FVector CamLoc;
	FVector Dir = Owner->GetActorForwardVector();
	if (APawn* Pawn = Cast<APawn>(Owner))
	{
		if (APlayerController* PC = Cast<APlayerController>(Pawn->GetController()))
		{
			FRotator CamRot;
			PC->GetPlayerViewPoint(CamLoc, CamRot);
			Dir = CamRot.Vector();
		}
		else
		{
			CamLoc = Owner->GetActorLocation() + FVector(0.f, 0.f, 60.f);
		}
	}
	else
	{
		CamLoc = Owner->GetActorLocation() + FVector(0.f, 0.f, 60.f);
	}

	const FVector TraceEnd = CamLoc + Dir * InteractDistance;

	FHitResult Hit;
	FCollisionQueryParams Params(SCENE_QUERY_STAT(TidebornInteract), false, Owner);
	bool bHit = GetWorld()->LineTraceSingleByChannel(Hit, CamLoc, TraceEnd, ECC_Visibility, Params);
	if (!bHit)
	{
		bHit = GetWorld()->LineTraceSingleByChannel(Hit, CamLoc, TraceEnd, ECC_WorldStatic, Params);
	}

	// Debug draw from the character forward along the *same* look direction —
	// never from the camera origin (that draws a fat blob into your face).
	const FVector DebugStart = Owner->GetActorLocation() + FVector(0.f, 0.f, 70.f);
	const FVector DebugEnd = DebugStart + Dir * InteractDistance;
	DrawDebugLine(GetWorld(), DebugStart, DebugEnd, bHit ? FColor::Green : FColor::Red, false, 1.0f, 0, 2.f);
	if (bHit)
	{
		DrawDebugPoint(GetWorld(), Hit.ImpactPoint, 12.f, FColor::Yellow, false, 1.0f);
	}

	AActor* Target = bHit ? Hit.GetActor() : nullptr;

	auto TryCallInteractable = [&](AActor* Candidate) -> bool
	{
		if (!Candidate)
		{
			return false;
		}
		if (ITidebornInteractable* Interactable = Cast<ITidebornInteractable>(Candidate))
		{
			Interactable->Tideborn_TryInteract(Owner);
			return true;
		}
		return false;
	};

	if (TryCallInteractable(Target))
	{
		return;
	}

	// Soft fallback: nearest gather node near the look point (no orange sphere spam)
	const FVector Probe = CamLoc + Dir * 180.f;
	TArray<FOverlapResult> Overlaps;
	FCollisionShape Sphere = FCollisionShape::MakeSphere(160.f);
	FCollisionQueryParams OverlapParams(SCENE_QUERY_STAT(TidebornInteractOverlap), false, Owner);
	GetWorld()->OverlapMultiByChannel(Overlaps, Probe, FQuat::Identity, ECC_WorldStatic, Sphere, OverlapParams);

	AActor* Best = nullptr;
	float BestDistSq = TNumericLimits<float>::Max();
	for (const FOverlapResult& O : Overlaps)
	{
		AActor* A = O.GetActor();
		if (!A || !Cast<ITidebornInteractable>(A))
		{
			continue;
		}
		const float DistSq = FVector::DistSquared(Probe, A->GetActorLocation());
		if (DistSq < BestDistSq)
		{
			BestDistSq = DistSq;
			Best = A;
		}
	}

	if (TryCallInteractable(Best))
	{
		return;
	}

	if (Target)
	{
		const FString Msg = FString::Printf(TEXT("Tideborn Interact -> %s (not gatherable)"), *Target->GetName());
		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(-1, 2.0f, FColor::Cyan, Msg);
		}
	}
	else if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(-1, 1.5f, FColor::Yellow, TEXT("Tideborn Interact -> look at a gather pillar + E"));
	}
}
