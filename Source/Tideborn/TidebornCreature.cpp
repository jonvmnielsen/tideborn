#include "TidebornCreature.h"
#include "TidebornInventoryComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/StaticMesh.h"
#include "UObject/ConstructorHelpers.h"
#include "Engine/Engine.h"
#include "Engine/World.h"

ATidebornCreature::ATidebornCreature()
{
	PrimaryActorTick.bCanEverTick = true;
	bUseControllerRotationYaw = false;

	GetCapsuleComponent()->InitCapsuleSize(42.f, 70.f);

	BodyMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BodyMesh"));
	BodyMesh->SetupAttachment(GetRootComponent());
	BodyMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	BodyMesh->ComponentTags.Add(FName(TEXT("TidebornBody")));

	GetCharacterMovement()->MaxWalkSpeed = 380.f;
	GetCharacterMovement()->bOrientRotationToMovement = true;
	AutoPossessAI = EAutoPossessAI::PlacedInWorldOrSpawned;
}

void ATidebornCreature::BeginPlay()
{
	Super::BeginPlay();
	Health = MaxHealth;
}

APawn* ATidebornCreature::FindPlayerPawn() const
{
	return UGameplayStatics::GetPlayerPawn(GetWorld(), 0);
}

void ATidebornCreature::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	AttackCooldownLeft = FMath::Max(0.f, AttackCooldownLeft - DeltaSeconds);

	if (CreatureRole == ETidebornCreatureRole::Threat && !bTamed)
	{
		TickThreat(DeltaSeconds);
	}
	else if (bTamed)
	{
		TickFollow(DeltaSeconds);
	}
}

void ATidebornCreature::TickThreat(float DeltaSeconds)
{
	APawn* Player = FindPlayerPawn();
	if (!Player)
	{
		return;
	}

	const float Dist = FVector::Dist(GetActorLocation(), Player->GetActorLocation());
	if (Dist > AggroRadius)
	{
		return;
	}

	AddMovementInput((Player->GetActorLocation() - GetActorLocation()).GetSafeNormal(), 1.f);

	if (Dist <= AttackRange && AttackCooldownLeft <= 0.f)
	{
		AttackCooldownLeft = AttackCooldown;
		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(94001, 1.5f, FColor::Red,
				FString::Printf(TEXT("%s snaps at you! (-%.0f threat)"), *DisplayName.ToString(), AttackDamage));
		}
		if (ACharacter* PC = Cast<ACharacter>(Player))
		{
			PC->LaunchCharacter((Player->GetActorLocation() - GetActorLocation()).GetSafeNormal() * 420.f + FVector(0, 0, 200), true, true);
		}
	}
}

void ATidebornCreature::TickFollow(float DeltaSeconds)
{
	APawn* Player = FindPlayerPawn();
	if (!Player)
	{
		return;
	}
	const float Dist = FVector::Dist(GetActorLocation(), Player->GetActorLocation());
	if (Dist > FollowDistance)
	{
		AddMovementInput((Player->GetActorLocation() - GetActorLocation()).GetSafeNormal(), 1.f);
	}
}

void ATidebornCreature::ApplyDamageFromPlayer(float Amount)
{
	Health = FMath::Max(0.f, Health - Amount);
	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(94002, 2.f, FColor::Orange,
			FString::Printf(TEXT("%s HP %.0f/%.0f"), *DisplayName.ToString(), Health, MaxHealth));
	}
}

bool ATidebornCreature::TryFeed(AActor* Interactor)
{
	if (CreatureRole != ETidebornCreatureRole::Tameable || bTamed)
	{
		return false;
	}

	UTidebornInventoryComponent* Inv = Interactor ? Interactor->FindComponentByClass<UTidebornInventoryComponent>() : nullptr;
	if (!Inv || !Inv->RemoveItem(BaitItemId, 1))
	{
		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(94003, 8.f, FColor::Orange,
				FString::Printf(TEXT("Need %s to feed %s (craft: Stick+Stone)"), *BaitItemId.ToString(), *DisplayName.ToString()));
		}
		return true;
	}

	++FeedsReceived;
	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(94003, 8.f, FColor::Green,
			FString::Printf(TEXT("Fed %s (%d/%d)"), *DisplayName.ToString(), FeedsReceived, FeedsNeededToTame));
	}

	if (FeedsReceived >= FeedsNeededToTame)
	{
		bTamed = true;
		GetCharacterMovement()->MaxWalkSpeed = 420.f;
		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(94004, 12.f, FColor::Cyan,
				FString::Printf(TEXT("%s TAMED - it will follow. Approach the Shore Gate."), *DisplayName.ToString()));
		}
	}
	return true;
}

bool ATidebornCreature::Tideborn_TryInteract(AActor* Interactor)
{
	if (CreatureRole == ETidebornCreatureRole::Tameable)
	{
		if (bTamed)
		{
			if (GEngine)
			{
				GEngine->AddOnScreenDebugMessage(94003, 6.f, FColor::Cyan,
					FString::Printf(TEXT("%s is tamed and following - use it at the Shore Gate"), *DisplayName.ToString()));
			}
			return true;
		}
		return TryFeed(Interactor);
	}

	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(94003, 4.f, FColor::Red,
			FString::Printf(TEXT("%s is hostile - stay clear or kite"), *DisplayName.ToString()));
	}
	return true;
}
