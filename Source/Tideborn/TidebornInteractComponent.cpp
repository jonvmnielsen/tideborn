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

UTidebornInteractComponent::UTidebornInteractComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
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

	const FVector Start = Owner->GetActorLocation() + FVector(0.f, 0.f, 60.f);
	const FVector End = Start + Owner->GetActorForwardVector() * InteractDistance;

	FHitResult Hit;
	FCollisionQueryParams Params(SCENE_QUERY_STAT(TidebornInteract), false, Owner);
	const bool bHit = GetWorld()->LineTraceSingleByChannel(Hit, Start, End, ECC_Visibility, Params);

	DrawDebugLine(GetWorld(), Start, End, bHit ? FColor::Green : FColor::Red, false, 1.5f, 0, 1.5f);

	if (bHit && Hit.GetActor())
	{
		AActor* Target = Hit.GetActor();
		if (ITidebornInteractable* Interactable = Cast<ITidebornInteractable>(Target))
		{
			Interactable->Tideborn_TryInteract(Owner);
			return;
		}

		const FString Msg = FString::Printf(TEXT("Tideborn Interact -> %s"), *Target->GetName());
		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(-1, 2.0f, FColor::Cyan, Msg);
		}
		UE_LOG(LogTemp, Log, TEXT("%s"), *Msg);
	}
	else if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(-1, 1.5f, FColor::Yellow, TEXT("Tideborn Interact -> (no hit)"));
	}
}
