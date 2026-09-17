#include "TidebornInteractComponent.h"
#include "TidebornInteractable.h"
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
	InteractDistance = 500.f;
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

	FCollisionQueryParams Params(SCENE_QUERY_STAT(TidebornInteract), false, Owner);

	// Prefer any interactable along the look ray (skip floor/walls if a gather node is behind/along path)
	TArray<FHitResult> Hits;
	GetWorld()->LineTraceMultiByChannel(Hits, CamLoc, TraceEnd, ECC_Visibility, Params);
	if (Hits.Num() == 0)
	{
		GetWorld()->LineTraceMultiByChannel(Hits, CamLoc, TraceEnd, ECC_WorldStatic, Params);
	}

	AActor* InteractableHit = nullptr;
	AActor* FirstHit = nullptr;
	FVector HitPoint = TraceEnd;
	for (const FHitResult& H : Hits)
	{
		AActor* A = H.GetActor();
		if (!A)
		{
			continue;
		}
		if (!FirstHit)
		{
			FirstHit = A;
			HitPoint = H.ImpactPoint;
		}
		if (Cast<ITidebornInteractable>(A))
		{
			InteractableHit = A;
			HitPoint = H.ImpactPoint;
			break;
		}
	}

	const FVector DebugStart = Owner->GetActorLocation() + FVector(0.f, 0.f, 70.f);
	DrawDebugLine(GetWorld(), DebugStart, DebugStart + Dir * InteractDistance, InteractableHit ? FColor::Green : FColor::Red, false, 1.0f, 0, 2.f);
	if (InteractableHit || FirstHit)
	{
		DrawDebugPoint(GetWorld(), HitPoint, 14.f, FColor::Yellow, false, 1.0f);
	}

	auto TryCall = [&](AActor* Candidate) -> bool
	{
		if (!Candidate)
		{
			return false;
		}
		if (ITidebornInteractable* I = Cast<ITidebornInteractable>(Candidate))
		{
			I->Tideborn_TryInteract(Owner);
			return true;
		}
		return false;
	};

	if (TryCall(InteractableHit))
	{
		return;
	}

	// Sphere around look point — catches pillars when crosshair is on upper body but ray grazed floor
	const FVector Probe = CamLoc + Dir * 220.f;
	TArray<FOverlapResult> Overlaps;
	FCollisionShape Sphere = FCollisionShape::MakeSphere(220.f);
	FCollisionQueryParams OverlapParams(SCENE_QUERY_STAT(TidebornInteractOverlap), false, Owner);
	GetWorld()->OverlapMultiByChannel(Overlaps, Probe, FQuat::Identity, ECC_Visibility, Sphere, OverlapParams);
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

	if (TryCall(Best))
	{
		return;
	}

	if (FirstHit && GEngine)
	{
		GEngine->AddOnScreenDebugMessage(91002, 6.f, FColor::Cyan,
			FString::Printf(TEXT("Look at a gather pillar (hit %s)"), *FirstHit->GetName()));
	}
	else if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(91002, 6.f, FColor::Yellow, TEXT("No gather target — aim nearer a pillar"));
	}
}


